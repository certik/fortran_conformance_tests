program ede_e_no_input_effect
  implicit none
! rule: S13.7.2.3.3-001
! covers: E-D-e-no-input-effect
  integer :: checks
  character(len=4) :: field
  real :: with_e, without_e
  checks = 0
  field = '1E+1'
  with_e = -99.0
  call expect_real(with_e, -99.0, 'sentinel-with-e')
  without_e = -88.0
  call expect_real(without_e, -88.0, 'sentinel-without-e')
  read(field,'(E4.0E2)') with_e
  read(field,'(E4.0)') without_e
  call expect_real(with_e, 10.0, 'with-e')
  call expect_real(without_e, 10.0, 'without-e')
  call expect_true(with_e == without_e, 'e-no-effect')
  if (checks /= 5) then
    write(*,'(a)') 'EDE:e_no_input_effect:check-total'
    error stop 1
  end if
  write(*,'(a)') 'E D EDITING E NO INPUT EFFECT OK'
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
end program ede_e_no_input_effect
