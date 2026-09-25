program i169p_lle_argument_controls
  implicit none
  character(len=1) :: string_a = '9'
  character(len=1) :: string_b = 'A'
  character(kind=kind('A'), len=1) :: same_a = '9'
  character(kind=kind('A'), len=1) :: same_b = 'A'
  call require_true('lle accepts default ascii string_a', lle(string_a, string_b))
  call require_true('lle uses same-kind character operands', lle(same_a, same_b))
  write(*,'(a)') 'INTRINSICS 16.9.P LLE ARGUMENT CONTROLS OK'
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
end program i169p_lle_argument_controls
