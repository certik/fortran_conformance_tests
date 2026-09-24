program i169e_char_roundtrip
  implicit none
  character(len=1) :: c, d, e
  integer :: i
  i = ichar('Q')
  c = char(i)
  d = char(ichar('K'), kind=kind('A'))
  e = char(ichar('Z'))
  call require_true('char integer argument in collating range', len(c) == 1 .and. c == 'Q')
  call require_true('char kind scalar constant argument', len(d) == 1 .and. d == 'K')
  call require_true('char result length one', len(char(ichar('Z'))) == 1)
  call require_true('char collating position result', ichar(c) == i)
  call require_true('ichar char integer roundtrip', ichar(char(i)) == i)
  call require_true('char ichar character roundtrip', len(char(ichar('Z'))) == 1 .and. char(ichar('Z')) == 'Z')
  write(*,'(a)') 'INTRINSICS 16.9.E CHAR CHARACTERISTICS OK'
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
end program i169e_char_roundtrip
