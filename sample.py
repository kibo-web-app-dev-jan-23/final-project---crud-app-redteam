def log_report(report):
  f= open("report.txt",'w',encoding = 'utf-8')
  f.write(f'{report}\n')
  f.close

error = "fuck_it"

log_report(error)