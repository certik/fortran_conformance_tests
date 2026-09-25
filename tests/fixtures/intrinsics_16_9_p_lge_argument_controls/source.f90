program i169p_lge_argument_controls
  implicit none
  character(len=1) :: string_a = 'A'
  character(len=1) :: string_b = '9'
  character(kind=kind('A'), len=1) :: same_a = 'A'
  character(kind=kind('A'), len=1) :: same_b = '9'
  call require_true('lge accepts default ascii string_a', lge(string_a, string_b))
  call require_true('lge uses same-kind character operands', lge(same_a, same_b))
  write(*,'(a)') 'INTRINSICS 16.9.P LGE ARGUMENT CONTROLS OK'
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
end program i169p_lge_argument_controls
