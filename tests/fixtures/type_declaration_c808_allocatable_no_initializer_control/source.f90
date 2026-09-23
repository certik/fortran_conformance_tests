program main
  implicit none
  integer, allocatable :: x
  if (allocated(x)) error stop
  print '(a)', 'type_declaration c808 allocatable control ok'
end program main
