program i169c_associated_inquiry_no_side_effect
  implicit none
  integer, target :: target_value = 41
  integer, pointer :: pointer_value
  logical :: before, after
  pointer_value => target_value
  before = associated(pointer_value)
  after = associated(pointer_value)
  call require_true('first inquiry true', before)
  call require_true('second inquiry true', after)
  call require_true('pointer remains associated', associated(pointer_value, target_value))
  call require_true('target value unchanged', target_value == 41)
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED INQUIRY NO SIDE EFFECT OK'
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
end program i169c_associated_inquiry_no_side_effect
