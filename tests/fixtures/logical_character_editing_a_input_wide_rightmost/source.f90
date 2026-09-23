program lce_a_input_wide_rightmost
  implicit none
! rule: S13.7.4-003
! covers: input-wide-field-rightmost
  integer :: checks
  character(len=4) :: field
  character(len=2) :: value
  integer :: guard
  checks = 0
  field = 'abcd'
  guard = 0
  call mark_text('wide-rightmost', value, guard, '??')
  call expect_pre_text(value, '??', guard, 'wide-rightmost')
  read(field,'(A4)') value
  call expect_text(value, 'cd', 'wide-rightmost')
  if (checks /= 2) then
    write(*,'(a)') 'LCE:a_input_wide_rightmost:check-total'
    error stop 1
  end if
  write(*,'(a)') 'LOGICAL CHARACTER EDITING A INPUT WIDE RIGHTMOST OK'
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
end program lce_a_input_wide_rightmost
