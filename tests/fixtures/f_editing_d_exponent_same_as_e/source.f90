program fe_d_exponent_same_as_e
  implicit none
! rule: S13.7.2.3.2-004
! covers: D-exponent-same-as-E-exponent
  integer :: checks
  character(len=4) :: e_field, d_field
  real :: e_value, d_value
  checks = 0
  e_field = '1E+1'
  d_field = '1D+1'
  e_value = -99.0
  call expect_real(e_value, -99.0, 'sentinel-e-control')
  d_value = -88.0
  call expect_real(d_value, -88.0, 'sentinel-d-control')
  read(e_field,'(F4.0)') e_value
  read(d_field,'(F4.0)') d_value
  call expect_real(e_value, 10.0, 'e-control')
  call expect_real(d_value, 10.0, 'd-control')
  call expect_true(d_value == e_value, 'd-same-e')
  if (checks /= 5) then
    write(*,'(a)') 'FE:d_exponent_same_as_e:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING D EXPONENT SAME AS E OK'
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
end program fe_d_exponent_same_as_e
