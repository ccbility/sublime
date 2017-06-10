import sublime
import sublime_plugin
import os.path


class DebugVarCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		file_name = self.view.file_name()
		ext = os.path.splitext(file_name)[1]
		# 获取文件的后缀，结果 .py .php .html .htm
		if ext == '.php':
			prefix = '$'
			sep = ';'
			deal_fun = 'var_dump'
			end = 'die;'
		elif ext == '.html' or ext == '.htm' or ext == '.js':
			prefix = ''
			sep = ';'
			deal_fun = 'console.log'
			end = 'return false;'

		i = 1
		total_len = len(self.view.sel())
		for region in self.view.sel():#所有光标所在的点
			# sublime.message_dialog(str(region.begin()))
			var_name = self.view.substr(self.view.word(region.begin()))
			debug_str = "\n" + deal_fun + '(' + prefix + var_name + ')' + sep;

			if i == total_len:
				debug_str += end
			debug_str += '\n'

			self.view.insert(edit, self.view.line(region).end(), debug_str)
			i += 1
			# sublime.message_dialog(str(len(self.view.sel())))
		self.view.run_command("move", {"by": "lines", "forward": True})		
		# sublime.message_dialog(str(len(self.view.sel())))		
