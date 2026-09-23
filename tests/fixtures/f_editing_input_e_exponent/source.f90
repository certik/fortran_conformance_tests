program fe_input_e_exponent
  implicit none
! rule: S13.7.2.3.2-003
! covers: F-input-E-exponent-form
  integer :: checks
  character(len=4) :: field
  real :: value
  checks = 0
  field = '1E+1'
  value = -99.0
  call expect_real(value, -99.0, 'sentinel-e-exponent')
  read(field,'(F4.0)') value
  call expect_real(value, 10.0, 'e-exponent')
  if (checks /= 2) then
    write(*,'(a)') 'FE:input_e_exponent:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING INPUT E EXPONENT OK'
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
end program fe_input_e_exponent
