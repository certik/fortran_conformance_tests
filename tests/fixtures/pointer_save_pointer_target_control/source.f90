program pointer_target_control
  implicit none
  integer, pointer :: p
  nullify(p)
  if (associated(p)) error stop
  print '(a)', 'POINTER TARGET CONTROL OK'
end program pointer_target_control
