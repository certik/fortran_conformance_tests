program i169c_associated_target_argument
  implicit none
  integer, target :: target_value = 29
  integer, target :: other_target = 31
  integer, pointer :: pointer_value, target_pointer
  pointer_value => target_value
  target_pointer => target_value
  call require_true('target entity with TARGET attribute', associated(pointer_value, target_value))
  call require_true('defined pointer target argument true', associated(pointer_value, target_pointer))
  target_pointer => other_target
  call require_false('defined pointer target argument false control', associated(pointer_value, target_pointer))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED TARGET ARGUMENT OK'
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
end program i169c_associated_target_argument
