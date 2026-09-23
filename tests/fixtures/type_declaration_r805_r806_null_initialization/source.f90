program main
  implicit none
  integer, target, save :: live_target
  integer, pointer :: ptr => null()
  live_target = 91
  if (associated(ptr)) error stop
  if (live_target /= 91) error stop
  print '(a)', 'type_declaration r805 null init ok'
end program main
