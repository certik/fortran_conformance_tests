module protected_attribute_target_definition_m
  implicit none
  integer, target :: storage = -9
  integer, pointer, protected :: data_ptr => null()
contains
  subroutine bind_storage()
    data_ptr => storage
  end subroutine
end module
program main
  use protected_attribute_target_definition_m, only: data_ptr, storage, bind_storage
  implicit none
  call bind_storage()
  if (.not. associated(data_ptr, storage)) error stop 1
  data_ptr = 23
  if (storage /= 23) error stop 2
  if (.not. associated(data_ptr, storage)) error stop 3
  write(*,'(a)') 'PROTECTED ATTRIBUTE TARGET DEFINITION CONTROL OK'
end program
