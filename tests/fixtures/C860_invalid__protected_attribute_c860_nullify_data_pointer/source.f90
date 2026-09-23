module protected_attribute_c860_nullify_m
  implicit none
  integer, pointer, protected :: p => null()
end module
program main
  use protected_attribute_c860_nullify_m, only: p
  implicit none
  nullify(p)
  if (associated(p)) error stop 1
  write(*,'(a)') 'PROTECTED ATTRIBUTE C860 NULLIFY DATA POINTER CONTROL OK'
end program
