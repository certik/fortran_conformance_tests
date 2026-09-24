program i169c_associated_status_inquiry
  implicit none
  integer, target :: target_value = 17
  integer, pointer :: pointer_value
  logical :: observed
  nullify(pointer_value)
  observed = .true.
  observed = associated(pointer_value)
  call require_false('status nullified false', observed)
  pointer_value => target_value
  observed = .false.
  observed = associated(pointer_value)
  call require_true('status assigned true', observed)
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED STATUS INQUIRY OK'
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
end program i169c_associated_status_inquiry
