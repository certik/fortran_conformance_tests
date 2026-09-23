program rm_required_rounding_modes
  implicit none
! rule: S13.7.2.3.8-003
! covers: round-up-conversion
! covers: round-down-conversion
! covers: round-zero-conversion
! covers: round-nearest-conversion
! covers: round-compatible-conversion
  integer :: checks
  real :: tie_positive, tie_negative, nearest_value
  character(len=5) :: up_field, down_field, zero_field, nearest_field, compatible_field
  checks = 0
  tie_positive = 1.25
  tie_negative = -1.25
  nearest_value = 1.125
  up_field = '#####'
  write(up_field,'(SS,RU,F5.1)') tie_positive
  call expect_text(up_field, '  1.3', 'round-up')
  down_field = '#####'
  write(down_field,'(SS,RD,F5.1)') tie_positive
  call expect_text(down_field, '  1.2', 'round-down')
  zero_field = '#####'
  write(zero_field,'(SS,RZ,F5.1)') tie_negative
  call expect_text(zero_field, ' -1.2', 'round-zero')
  nearest_field = '#####'
  write(nearest_field,'(SS,RN,F5.1)') nearest_value
  call expect_text(nearest_field, '  1.1', 'round-nearest')
  compatible_field = '#####'
  write(compatible_field,'(SS,RC,F5.1)') tie_negative
  call expect_text(compatible_field, ' -1.3', 'round-compatible')
  if (checks /= 5) then
    write(*,'(a)') 'RM:required_rounding_modes:check-total'
    error stop 1
  end if
  write(*,'(a)') 'ROUNDING MODE REQUIRED ROUNDING MODES OK'
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
end program rm_required_rounding_modes
