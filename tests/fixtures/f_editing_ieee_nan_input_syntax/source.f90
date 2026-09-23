program fe_ieee_nan_input_syntax
  use, intrinsic :: ieee_arithmetic
  implicit none
! rule: S13.7.2.3.2-006
! covers: ieee-nan-input-syntax
  integer :: checks
  character(len=5) :: field
  real :: value
  checks = 0
  field = 'NAN()'
  value = -99.0
  call expect_real(value, -99.0, 'sentinel-nan-empty')
  read(field,'(F5.0)') value
  call expect_true(ieee_is_nan(value), 'nan-empty')
  if (checks /= 2) then
    write(*,'(a)') 'FE:ieee_nan_input_syntax:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING IEEE NAN INPUT SYNTAX OK'
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
end program fe_ieee_nan_input_syntax
