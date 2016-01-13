import os
import datetime
import logging

from django.template import Context
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode

Global = {"config": {}, "projects": []}

Global["config"]["path"] = "projects"
Global["config"]["date_format"] = "%d-%m-%Y"
Global["config"]["project_body_block"] = "body"


def preBuild(site):

	global Global

	# Check if the projects path exists
	page_path = os.path.join(site.page_path, Global["config"]["path"])

	if not os.path.isdir(page_path):
		logging.warning("No projects folder found at: %s", page_path)

	for page in site.pages():

		if page.path.startswith("%s/" % Global["config"]["path"]):

			if not page.path.endswith('.html'):
				continue

			context = page.context()
			context_project = {"path": "/%s" % page.path}

			# Check if we have the required keys
			for field in ["title", "date", "tags", "thumbnail", "full", "pri_colour", "sec_colour", "published"]:

				if not context.has_key(field):
					logging.warning("Page %s is missing field: %s" % (page.path, field))
				else:

					if field == "date":
						context_project[field] = _convertDate(context[field], page.path)
					else:
						context_project[field] = context[field]

			# Temp post context
			temp_project_context = Context(context)
			temp_project_context.update(context_project)

			# Add the post contents
			context_project["body"] = _get_node(
				get_template(page.path),
				context=temp_project_context,
				name=Global["config"]["project_body_block"])
			if context_project["published"] == "true":
				Global["projects"].append(context_project)

	# Sort the projects by date and add the next and previous page indexes
	Global["projects"] = sorted(Global["projects"], key=lambda x: x.get("date"))
	Global["projects"].reverse()

	indexes = xrange(0, len(Global["projects"]))

	for i in indexes:
		if i+1 in indexes: Global["projects"][i]['prevProject'] = Global["projects"][i+1]
		if i-1 in indexes: Global["projects"][i]['nextProject'] = Global["projects"][i-1]


def preBuildPage(site, page, context, data):

	context['year'] = datetime.datetime.now().year
	context['projects'] = Global["projects"]

	for project in Global["projects"]:
		if page.path in project["path"]:
			context.update(project)

	return context, data


# Utilities for the functions above

def _convertDate(date_string, path):
	# Convert a string to a date object
	try:
		return datetime.datetime.strptime(date_string,
			Global["config"]["date_format"])
	except Exception, e:
		logging.warning("Date format not correct for page %s, should be %s\n%s" \
			% (path, Global["config"]["date_format"], e))

def _get_node(template, context=Context(), name='subject'):
	# Get the contents of a block in a specific template
	for node in template:
		if isinstance(node, BlockNode) and node.name == name:
			return node.render(context)
		elif isinstance(node, ExtendsNode):
			return _get_node(node.nodelist, context, name)
	raise Exception("Node '%s' could not be found in template." % name)
