program main
  implicit none
  integer, parameter :: a=1, b=a+1
  if (b /= 2) error stop
  print '(a)', 'type_declaration c807 all initialized ok'
end program main
