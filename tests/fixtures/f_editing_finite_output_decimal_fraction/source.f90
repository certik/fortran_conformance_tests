program fe_finite_output_decimal_fraction
  implicit none
! rule: S13.7.2.3.2-012
! covers: F-finite-output-decimal-symbol
! covers: F-finite-output-d-fractional-digits
  integer :: checks
  real :: value
  character(len=5) :: field
  checks = 0
  value = 1.25
  field = '#####'
  write(field,'(SS,F5.2)') value
  call expect_text(field, ' 1.25', 'decimal-fraction')
  if (checks /= 1) then
    write(*,'(a)') 'FE:finite_output_decimal_fraction:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING FINITE OUTPUT DECIMAL FRACTION OK'
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
end program fe_finite_output_decimal_fraction
