#coding: utf-8
import sublime
import sublime_plugin
import os.path
import re
import collections

def count_indent(line_cont):
	#不光是空格，还可能两者一起混合存在,所以不能分情况，必须一起统计出来
	match_cont = re.match(r'((\s*\t*)*)', line_cont)
	return match_cont.group(1)

class DebugVarCommand(sublime_plugin.TextCommand):
	#问题：
	def run(self, edit):
		file_name = self.view.file_name()
		ext = os.path.splitext(file_name)[1]
		# 获取文件的后缀，结果 .py .php .html .htm
		if ext == '.php':
			prex = '$'
			sep = ';'
			deal_fun = 'var_dump'
			end = 'die;'
		elif ext == '.html' or ext == '.htm' or ext == '.js':
			prex = ''
			sep = ';'
			deal_fun = 'console.log'
			end = 'return false;'
		elif ext == '.py':
			prex = ''
			sep = ';'
			deal_fun = 'print'
			end = 'exit();'
		else:
			exit()

		i = 1
		total_len = len(self.view.sel())
		move_bool = True
		all_str = collections.OrderedDict()#有序字典
		for region in self.view.sel():#所有光标所在的点
			# sublime.message_dialog(str(var_name))
			var_name = self.view.substr(self.view.word(region.begin()))
			line_cont = self.view.substr(self.view.line(region.begin()))

			sep_pos = self.view.find(r'[' + sep + ']{1}$', region.begin());

			# 如果当前行为空，那么直接输出结束符
			# 如果含 M D 这样的Thinkphp函数名，那么输出 getLastSql 或 _sql
			# 
			# python可以边赋值边判断真假？
			sql_match = re.match(r'.*([DM]{1}\([\s\'\"]*?' + var_name + '.*?\))\s*-', line_cont)
			this_var = re.match(r'.*?(\$this->' + var_name + ')', line_cont)
			var_sql = re.match(r'.*([DM]{1})\(\$' + var_name + '\)', line_cont)
			# sublime.message_dialog(str(this_var))
			if sql_match:
				tp_m = sql_match.group(1)
			else:
				tp_m = False

			indent_str = count_indent(line_cont)

			if line_cont == '':
				debug_str = ''	
				move_bool = False
				#当前行为空时，直接输出一个结束符

			#处理php中，$this->这种情况
			elif this_var:
				debug_str = "\n" + indent_str + deal_fun + '($this->'+ var_name + ')' + sep;
			elif tp_m:
				debug_str = '\n' + indent_str + deal_fun + '(' + tp_m + '->_sql());'
			elif var_sql:
				debug_str = "\n" + indent_str + deal_fun + '(' + prex + var_name + ', ' + var_sql.group(1) + '(' + prex + var_name + ')->_sql()' + ')' + sep;
			else:
				debug_str = "\n" + indent_str + deal_fun + '(' + prex + var_name + ')' + sep;

			if i == total_len:
				debug_str += end

			if sep_pos:
				pos = sep_pos.end()
			else:
				pos = self.view.line(region).end()
			if pos in all_str.keys():
				all_str[pos] += debug_str.strip()
			else:
				all_str[pos] = debug_str
			# self.view.insert(edit, self.view.line(region).end(), debug_str)
			i += 1

		#循环输出要调试的代码
		# sublime.message_dialog(str(all_str))
		offset = 0 #我们自己插入的字符，会影响后面要插入字符的定位
		#要按照key的大小输出，不然乱序
		for k in all_str:
			self.view.insert(edit, k + offset, all_str[k])
			offset += len(all_str[k])
		if move_bool:
			#为了解决一行字符过长导致定位错误的问题，先让它走到行尾再press down
			self.view.run_command("move_to", {"to": "hardeol"})	
			self.view.run_command("move", {"by": "lines", "forward": True})	