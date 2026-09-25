program i169p_llt_ascii_values
  implicit none
  character(len=1) :: short_a = 'A'
  character(len=2) :: a_blank = 'A '
  character(len=2) :: a_exclaim = 'A!'
  character(len=2) :: eq_a = 'AZ'
  character(len=2) :: eq_b = 'AZ'
  character(len=0) :: empty_a = ''
  character(len=0) :: empty_b = ''
  character(len=1) :: digit = '9'
  character(len=1) :: upper_a = 'A'
  character(len=1) :: upper_z = 'Z'
  character(len=1) :: underscore = '_'
  character(len=1) :: lower_a = 'a'
  character(len=3) :: one = 'ONE'
  character(len=3) :: two = 'TWO'
  call require_true('llt blank padding lengths', &
       len(short_a) == 1 .and. len(a_blank) == 2 .and. len(a_exclaim) == 2)
  call require_true('llt shorter left precedes exclaim', llt(short_a, a_exclaim))
  call require_false('llt padded equality false', llt(short_a, a_blank))
  call require_false('llt equal nonempty strings false', &
       llt(eq_a, eq_b))
  call require_false('llt equal zero length strings false', &
       llt(empty_a, empty_b))
  call require_true('llt ascii precedes true', &
       llt(digit, upper_a) .and. llt(upper_a, lower_a) .and. &
       llt(upper_z, lower_a) .and. llt(upper_z, underscore) .and. llt(one, two))
  call require_false('llt ascii follows false', &
       llt(upper_a, digit) .or. llt(lower_a, upper_a) .or. &
       llt(lower_a, upper_z) .or. llt(underscore, upper_z))
  write(*,'(a)') 'INTRINSICS 16.9.P LLT ASCII VALUES OK'
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
end program i169p_llt_ascii_values
