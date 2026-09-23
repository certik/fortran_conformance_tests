program rm_decimal_internal_directions
  implicit none
! rule: S13.7.2.3.8-002
! covers: decimal-value-defined
! covers: internal-value-defined
! covers: formatted-output-conversion-direction
! covers: formatted-input-conversion-direction
  integer :: checks
  character(len=4) :: input_field
  character(len=5) :: output_field
  real :: input_value, output_value
  checks = 0
  input_field = '1.25'
  input_value = -99.0
  call expect_real(input_value, -99.0, 'sentinel-input-value')
  read(input_field,'(F4.2)') input_value
  call expect_real(input_value, 1.25, 'input-decimal-to-internal')
  output_value = 1.125
  output_field = '#####'
  write(output_field,'(SS,F5.3)') output_value
  call expect_text(output_field, '1.125', 'output-internal-to-decimal')
  if (checks /= 3) then
    write(*,'(a)') 'RM:decimal_internal_directions:check-total'
    error stop 1
  end if
  write(*,'(a)') 'ROUNDING MODE DECIMAL INTERNAL DIRECTIONS OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'RM:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'RM:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_real(observed, expected, label)
    real, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'RM:real', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_real
end program rm_decimal_internal_directions
