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
			line_end = '[;{]'
			func_mark = 'function'
			sep = ';'
			deal_fun = 'var_dump'
			end = 'die;'
		elif ext == '.html' or ext == '.htm' or ext == '.js':
			prex = ''
			line_end = '.'
			func_mark = 'function'
			sep = ';'
			deal_fun = 'console.log'
			end = 'return false;'
		elif ext == '.py':
			prex = ''
			line_end = '\r\n'
			func_mark = 'def:'
			sep = ';'
			deal_fun = 'print'
			end = 'exit();'
		else:
			exit()

		i = 1
		total_len = len(self.view.sel())
		move_bool = True
		all_str = collections.OrderedDict()#有序字典
		all_str_indent = collections.OrderedDict()#有序字典对应的缩进
		for region in self.view.sel():#所有光标所在的点
			var_name = self.view.substr(self.view.word(region.begin()))
			area_var = self.view.substr(region) # 光标所包裹的内容
			line_cont = self.view.substr(self.view.line(region.begin()))

			# 考虑到 $ // 的注释情况
			# sep_pos = self.view.find(r'[' + line_end + ']{1}[^\r\n]*$', region.begin());
			# sep_pos = self.view.find(r'\s*?[' + line_end + ']{1}', region.begin());
			sep_pos = self.view.find(r'.{1}(?<=' + line_end + '{1})', region.begin());
			# sep_pos = self.view.find(r'%s{1}(?=\s{1})' % line_end, region.begin());
			# self.view.find 是一直往下查找，直到找到
			is_func = line_cont.find(func_mark)

			indent_str = count_indent(line_cont)
			if is_func != -1:
				indent_str += '    '

			# 如果当前行为空，那么直接输出结束符
			# 如果含 M D 这样的Thinkphp函数名，那么输出 getLastSql 或 _sql
			# 
			# python可以边赋值边判断真假？
			if not area_var:
				sql_match = re.match(r'.*([DM]{1}\([\s\'\"]*?' + var_name + '.*?\))\s*-', line_cont)
				C_match = re.match(r'.*([C]{1}\([\s\'\"]*?' + var_name + '.*?\))\s*', line_cont)
				this_var = re.match(r'.*?(\$this->' + var_name + ')', line_cont)
				var_sql = re.match(r'.*([DM]{1})\(\$' + var_name + '\)', line_cont)
				# sublime.message_dialog(str(C_match))
				if sql_match:
					tp_m = sql_match.group(1)
				else:
					tp_m = False

				if C_match:
					tp_c = C_match.group(1)
				else:
					tp_c = False

			pos_bool = False

			#处理php中，$this->这种情况
			if line_cont == '':
				debug_str = ''	
				pos_bool = True
			elif area_var:
				# debug_str = "\n" + indent_str + deal_fun + '('+ area_var + ')' + sep;
				debug_str = '\n%s%s(%s)%s' % (indent_str, deal_fun, area_var, sep)
			elif this_var:
				debug_str = "\n" + indent_str + deal_fun + '($this->'+ var_name + ')' + sep;
			elif tp_m:
				debug_str = '\n' + indent_str + deal_fun + '(' + tp_m + '->_sql());'
			elif tp_c:
				debug_str = '\n' + indent_str + deal_fun + '(' + tp_c + ');'
			elif var_sql:
				debug_str = "\n" + indent_str + deal_fun + '(' + prex + var_name + ', ' + var_sql.group(1) + '(' + prex + var_name + ')->_sql()' + ')' + sep;
			else:
				debug_str = "\n" + indent_str + deal_fun + '(' + prex + var_name + ')' + sep;

			if i == total_len:
				debug_str += end

			if pos_bool:
				pos = self.view.line(region).begin()
			elif sep_pos:
				pos = sep_pos.end()
			else:
				pos = self.view.line(region).end()
			if pos in all_str.keys():
				all_str[pos] += debug_str.strip()
			else:
				all_str[pos] = debug_str
				all_str_indent[pos] = len(indent_str) # 为了光标和输出的字符对齐
			# self.view.insert(edit, self.view.line(region).end(), debug_str)
			i += 1

		#循环输出要调试的代码
		# sublime.message_dialog(str(all_str))
		offset = 0 #我们自己插入的字符，会影响后面要插入字符的定位
		#要按照key的大小输出，不然乱序
		
		# 清空光标
		self.view.sel().clear()
		
		for k in all_str:
			tmp_pos = k + offset
			self.view.insert(edit, tmp_pos, all_str[k])
			offset += len(all_str[k])
			self.view.sel().add(sublime.Region(tmp_pos + 1 + all_str_indent[k]))