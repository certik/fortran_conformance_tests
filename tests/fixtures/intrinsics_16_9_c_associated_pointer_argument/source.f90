program i169c_associated_pointer_argument
  implicit none
  integer, target :: target_value = 23
  integer, pointer :: pointer_value
  nullify(pointer_value)
  call require_false('defined null pointer status', associated(pointer_value))
  pointer_value => target_value
  call require_true('defined associated pointer status', associated(pointer_value))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED POINTER ARGUMENT OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169c_associated_pointer_argument
