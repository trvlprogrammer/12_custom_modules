# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta
import datetime
import json
import math
import pytz


class DependingTasks(models.Model):
    _name = "dhx_gantt.task.relation"
    _description = "The many2many table that has extra info (relation_type)"

    task_id = fields.Many2one('project.task', required=True)
    project_id = fields.Many2one(related='task_id.project_id')
    related_task_id = fields.Many2one('project.task', required=True)
    relation_type = fields.Selection([
        ("0", "Finish to Start"),
        ("1", "Start to Start"),
        ("2", "Finish to Finish"),
        ("3", "Start to Finish")
    ], default="0", required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done')], default='draft')

    _sql_constraints = [
        ('task_relation_unique', 'unique(task_id, related_task_id)', 'Two tasks can have only one relation!'),
    ]


class Task(models.Model):
    _inherit = "project.task"
    _order = 'main_sequence'
    
    main_sequence = fields.Integer('Main Sequence', compute="_compute_main_sequence", readonly=True, store=True)
    
    delta = fields.Integer(string='Completion Delta')
    weight = fields.Integer(string='Completion Weight')
    sort_flag = fields.Boolean("Sorter")
        
    @api.multi
    def _compute_main_sequence(self):
        for t in self:
            t.main_sequence = (t.stage_id.sequence + 1) * 100 + t.sequence + 1
           
    task_code = fields.Char("Task Code")
    job_id = fields.Many2one('hr.job', 'Operator Role')
    subscription_template_id = fields.Many2one('sale.subscription.template', 'Schedule')
    lag_time = fields.Integer('Before Time')    
    
    recurrence = fields.Selection([
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('otherday', 'Every Other Day'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ], default='daily')
    
    successor_task_ids = fields.One2many('dhx_gantt.task.relation', 'task_id')
    predecessor_task_ids = fields.One2many('dhx_gantt.task.relation', 'related_task_id')
    links_serialized_json = fields.Char('Serialized Links JSON', compute="compute_links_json")

    @api.model
    def get_dependency_tasks(self, task, recursive=False):
        dependency_tasks = task.with_context(
            prefetch_fields=False,
        ).predecessor_task_ids
        if recursive:
            for t in dependency_tasks:
                dependency_tasks |= self.get_dependency_tasks(t, recursive)
        return dependency_tasks

    @api.multi
    def compute_links_json(self):
        for r in self:
            links = []
            r.links_serialized_json = '['
            for link in r.predecessor_task_ids:
                json_obj = {
                    'id': link.id,
                    'source': link.task_id.id,
                    'target': link.related_task_id.id,
                    'type': link.relation_type
                }
                links.append(json_obj)
            r.links_serialized_json = json.dumps(links)

    def duration_between_dates(self, date_from, date_to):
        return (date_to - date_from).days

    def add_days(self, target_date, days):
        return target_date + timedelta(days=days)

    @api.multi
    def compute_critical_path(self):
        # evidently the critical path is the longest path on the network graph
        # evidently this algorithm does not work

        # project = self.project_id
        # tasks = project.task_ids.sorted('date_start')
        tasks = self

        critical_path = []
        critical_tasks = []
        critical_links = []
        # last_end_date = False
        current_task = tasks and tasks[0] or False
        while current_task:
            critical_path.append(current_task)
            critical_tasks.append(current_task.id)

            sorted_by_sequence = current_task.successor_task_ids.sorted(lambda dep: dep.related_task_id.sequence, reverse=False)
            if sorted_by_sequence:
                current_task = sorted_by_sequence[0].related_task_id
                critical_links.append(sorted_by_sequence[0].id)
            else:
                current_task = False

        # print('critical_path')
        txt = ''
        for path in critical_path:
            txt += str(path.date_start) + ' >> '
        # print(txt)
        return {
            'tasks': critical_tasks,
            'links': critical_links
        }

    @api.multi
    def bf_traversal_schedule(self):
        projects = self.mapped('project_id')
        if len(projects) > 1:
            raise UserError("Can't auto schedule more than one project in the same time.")

        # not using project.task_ids because it has a default domain
        tasks = self.env['project.task'].search([('project_id', '=', projects.id)])
        leading_tasks = tasks.filtered(lambda t: not t.predecessor_task_ids)

        # Mark all the vertices as not visited
        visited = []

        # print('LEADING TASKS are ', len(leading_tasks))
        # print(leading_tasks.mapped('name'))
        # Breadth First Traversal for every task that have no dependency
        for task in leading_tasks:
            # Create a queue for BFS
            queue = []
            queue.append(task)
            traversal_counter = 0
            # visited.append(task.id)
            while queue:
                traversal_counter += 1
                if traversal_counter > 4069:
                    # break out of a possibly infinite loop
                    # print('# break out of a possibly infinite loop')
                    break
                # Dequeue a vertex from
                # queue and print it
                s = queue.pop(0)
                # print('JUST POPPED')
                # print(s.name)
                s.schedule(visited)
                visited.append(s.id)
                # Get all adjacent vertices of the
                # dequeued vertex s. If a adjacent
                # has not been visited, then mark it
                # visited and enqueue it
                for child in s.successor_task_ids:
                    if child.related_task_id.id not in visited:
                        queue.append(child.related_task_id)
                        # visited.append(child.related_task_id.id)

    @api.multi
    def set_date_end(self):
        self.date_end = self.date_start + datetime.timedelta(hours=self.planned_hours)

    @api.multi
    def schedule(self, visited):
        # print('Rescheduling task ', self and self.name or 'NONE')
        self.ensure_one()
        if not self.predecessor_task_ids:
            # print('No dependencies')
            # TODO: adjust datetime for server vs local timezone
            if self.project_id and self.project_id.date_start:
                # print('setting date to project\'s')
                self.date_start = self.project_id.date_start + self.lag_time
                self.set_date_end()
        for parent in self.predecessor_task_ids:
            # print('found dependency on ', parent)
            date_start = parent.task_id.date_start
            if not date_start:
                continue
            date_end = date_start + datetime.timedelta(hours=parent.task_id.planned_hours)
            # print('schedule task {0} based on parent {1}'.format(self.name, parent.task_id.name))
            # print('parnet starts at {0} and ends at {1}'.format(date_start, date_end))
            if parent.relation_type == "0":  # Finish to Start
                if date_end:
                    todo_date_start = date_end + datetime.timedelta(hours=1 + self.lag_time)
                    # print('todo_date_start = {0}'.format(todo_date_start))
                    if self.id in visited:
                        self.date_start = max(todo_date_start, self.date_start)
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
                    else:
                        self.date_start = todo_date_start
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
            elif parent.relation_type == "1":  # Start to Start
                if date_start:
                    todo_date_start = date_start + datetime.timedelta(self.lag_time)
                    # print('todo_date_start = {0}'.format(todo_date_start))
                    if self.id in visited:
                        self.date_start = max(todo_date_start, self.date_start)
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
                    else:
                        self.date_start = todo_date_start
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
            elif parent.relation_type == "2":  # Finish to Finish
                if date_end:
                    todo_date_start = date_end - datetime.timedelta(self.planned_hours + self.lag_time)
                    # print('todo_date_start = {0}'.format(todo_date_start))
                    if self.id in visited:
                        self.date_start = max(todo_date_start, self.date_start)
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
                    else:
                        self.date_start = todo_date_start
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
            elif parent.relation_type == "3":  # Start to Finish
                if date_end:
                    todo_date_start = date_start - datetime.timedelta(self.planned_hours + self.lag_time)
                    # print('todo_date_start = {0}'.format(todo_date_start))
                    if self.id in visited:
                        self.date_start = max(todo_date_start, self.date_start)
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
                    else:
                        self.date_start = todo_date_start
                        set_date_end = getattr(self, "set_date_end", None)
                        if callable(set_date_end):
                            self.set_date_end()
                        # print('setting date_start to {0}'.format(self.date_start))
