program fe_field_width_fixed_selected
  implicit none
! rule: S13.7.2.3.2-001
! covers: F-field-width
  integer :: checks
  real :: negative_value, positive_value
  character(len=5) :: fixed
  character(len=3) :: selected
  checks = 0
  negative_value = -3.0
  positive_value = 3.0
  fixed = '#####'
  write(fixed,'(SS,F5.1)') negative_value
  call expect_text(fixed, ' -3.0', 'f5-1-fixed')
  selected = '###'
  write(selected,'(SS,F0.1)') positive_value
  call expect_text(selected, '3.0', 'f0-1-selected')
  if (checks /= 2) then
    write(*,'(a)') 'FE:field_width_fixed_selected:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING FIELD WIDTH FIXED SELECTED OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'FE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'FE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_real(observed, expected, label)
    real, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'FE:real', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_real
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'FE:logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
end program fe_field_width_fixed_selected
