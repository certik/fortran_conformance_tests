module protected_attribute_c860_assign_m
  implicit none
  integer, pointer, protected :: p => null()
end module
program main
  use protected_attribute_c860_assign_m, only: p
  implicit none
  integer, target :: local
  local = 2
  p => local
  if (.not. associated(p, local)) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C860 DATA POINTER ASSIGNMENT CONTROL OK'
end program
