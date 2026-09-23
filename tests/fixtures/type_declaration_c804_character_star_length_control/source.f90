program main
  implicit none
  character :: text*3
  text = 'abc'
  if (len(text) /= 3) error stop
  if (text /= 'abc') error stop
  print '(a)', 'type_declaration c804 character length ok'
end program main
