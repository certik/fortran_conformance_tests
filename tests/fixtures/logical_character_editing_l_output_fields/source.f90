program lce_l_output_fields
  implicit none
! rule: S13.7.3-004
! covers: true-output-field
! covers: false-output-field
  integer :: checks
  logical :: true_value, false_value
  character(len=3) :: true_field
  character(len=2) :: false_field
  checks = 0
  true_value = .true.
  false_value = .false.
  true_field = '###'
  write(true_field,'(L3)') true_value
  call expect_text(true_field, '  T', 'l3-true')
  false_field = '##'
  write(false_field,'(L2)') false_value
  call expect_text(false_field, ' F', 'l2-false')
  if (checks /= 2) then
    write(*,'(a)') 'LCE:l_output_fields:check-total'
    error stop 1
  end if
  write(*,'(a)') 'LOGICAL CHARACTER EDITING L OUTPUT FIELDS OK'
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
end program lce_l_output_fields
