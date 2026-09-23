program fe_infinity_output_narrow
  use, intrinsic :: ieee_arithmetic
  implicit none
! rule: S13.7.2.3.2-010
! covers: infinity-output-inf-form-when-narrow
! covers: infinity-output-asterisks-when-too-narrow
  integer :: checks
  real :: value
  character(len=4) :: inf_field
  character(len=2) :: star_field
  checks = 0
  value = ieee_value(0.0, ieee_positive_inf)
  inf_field = '####'
  write(inf_field,'(SS,F4.1)') value
  call expect_text(inf_field, ' Inf', 'inf-f4-1')
  star_field = '##'
  write(star_field,'(SS,F2.1)') value
  call expect_text(star_field, '**', 'inf-f2-1')
  if (checks /= 2) then
    write(*,'(a)') 'FE:infinity_output_narrow:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING INFINITY OUTPUT NARROW OK'
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
end program fe_infinity_output_narrow
