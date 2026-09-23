program lce_a_input_short_left_justified
  implicit none
! rule: S13.7.4-003
! covers: input-short-field-left-justified
  integer :: checks
  character(len=2) :: field
  character(len=4) :: value
  integer :: guard
  checks = 0
  field = 'xy'
  guard = 0
  call mark_text('short-left', value, guard, '????')
  call expect_pre_text(value, '????', guard, 'short-left')
  read(field,'(A2)') value
  call expect_text(value, 'xy  ', 'short-left')
  if (checks /= 2) then
    write(*,'(a)') 'LCE:a_input_short_left_justified:check-total'
    error stop 1
  end if
  write(*,'(a)') 'LOGICAL CHARACTER EDITING A INPUT SHORT LEFT JUSTIFIED OK'
contains
  subroutine mark_logical(name, value, guard, sentinel)
    character(len=*), intent(in) :: name
    logical, intent(out) :: value
    integer, intent(out) :: guard
    logical, intent(in) :: sentinel
    if (len(name) == 0) error stop 1
    value = sentinel
    guard = 1
  end subroutine mark_logical
  subroutine mark_text(name, value, guard, sentinel)
    character(len=*), intent(in) :: name
    character(len=*), intent(out) :: value
    integer, intent(out) :: guard
    character(len=*), intent(in) :: sentinel
    if (len(name) == 0) error stop 1
    value = sentinel
    guard = 1
  end subroutine mark_text
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'LCE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'LCE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_logical(observed, expected, label)
    logical, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed .neqv. expected) then
      write(*,'(a,1x,a)') 'LCE:logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_logical
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'LCE:int', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_int
  subroutine expect_pre_logical(observed, expected, guard, label)
    logical, intent(in) :: observed, expected
    integer, intent(in) :: guard
    character(len=*), intent(in) :: label
    if (guard /= 1) then
      write(*,'(a,1x,a)') 'LCE:pre-logical', label
      error stop 1
    end if
    if (observed .neqv. expected) then
      write(*,'(a,1x,a)') 'LCE:pre-logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_pre_logical
  subroutine expect_pre_text(observed, expected, guard, label)
    character(len=*), intent(in) :: observed, expected, label
    integer, intent(in) :: guard
    if (guard /= 1) then
      write(*,'(a,1x,a)') 'LCE:pre-text', label
      error stop 1
    end if
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'LCE:pre-text', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'LCE:pre-text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_pre_text
end program lce_a_input_short_left_justified
