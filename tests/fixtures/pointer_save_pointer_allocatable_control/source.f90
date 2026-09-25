program pointer_allocatable_control
  implicit none
  integer, pointer :: p
  nullify(p)
  if (associated(p)) error stop
  print '(a)', 'POINTER ALLOCATABLE CONTROL OK'
end program pointer_allocatable_control
