program fe_infinity_output_wide
  use, intrinsic :: ieee_arithmetic
  implicit none
! rule: S13.7.2.3.2-010
! covers: infinity-output-right-justified
! covers: infinity-output-infinity-form-when-wide
  integer :: checks
  real :: value
  character(len=9) :: field
  checks = 0
  value = ieee_value(0.0, ieee_positive_inf)
  field = '#########'
  write(field,'(SS,F9.1)') value
  call expect_text(field, ' Infinity', 'inf-f9-1')
  if (checks /= 1) then
    write(*,'(a)') 'FE:infinity_output_wide:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING INFINITY OUTPUT WIDE OK'
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
end program fe_infinity_output_wide
