program ede_input_same_as_f
  implicit none
! rule: S13.7.2.3.3-002
! covers: E-D-input-same-as-F
  integer :: checks
  character(len=2) :: field
  real :: e_value, d_value
  checks = 0
  field = '15'
  e_value = -99.0
  call expect_real(e_value, -99.0, 'sentinel-e-input')
  d_value = -88.0
  call expect_real(d_value, -88.0, 'sentinel-d-input')
  read(field,'(E2.1)') e_value
  read(field,'(D2.1)') d_value
  call expect_real(e_value, 1.5, 'e-input')
  call expect_real(d_value, 1.5, 'd-input')
  call expect_true(e_value == d_value, 'e-d-input-same')
  if (checks /= 5) then
    write(*,'(a)') 'EDE:input_same_as_f:check-total'
    error stop 1
  end if
  write(*,'(a)') 'E D EDITING INPUT SAME AS F OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'EDE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'EDE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_one_of(observed, first, second, third, label)
    character(len=*), intent(in) :: observed, first, second, third, label
    if (len(observed) /= len(first) .or. len(observed) /= len(second) .or. len(observed) /= len(third)) then
      write(*,'(a,1x,a)') 'EDE:length', label
      error stop 1
    end if
    if (observed /= first .and. observed /= second .and. observed /= third) then
      write(*,'(a,1x,a)') 'EDE:one-of', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_one_of
  subroutine expect_either(observed, first, second, label)
    character(len=*), intent(in) :: observed, first, second, label
    if (len(observed) /= len(first) .or. len(observed) /= len(second)) then
      write(*,'(a,1x,a)') 'EDE:length', label
      error stop 1
    end if
    if (observed /= first .and. observed /= second) then
      write(*,'(a,1x,a)') 'EDE:either', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_either
  subroutine expect_real(observed, expected, label)
    real, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'EDE:real', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_real
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'EDE:logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
end program ede_input_same_as_f
