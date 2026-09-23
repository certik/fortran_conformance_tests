program ede_scale_positive
  implicit none
! rule: S13.7.2.3.3-006
! covers: E-D-scale-positive-normalization
  integer :: checks
  real :: value
  character(len=10) :: field
  checks = 0
  value = 1.0
  field = '##########'
  write(field,'(SS,1P,E10.3E2)') value
  call expect_text(field, ' 1.000E+00', 'field')
  if (checks /= 1) then
    write(*,'(a)') 'EDE:scale_positive:check-total'
    error stop 1
  end if
  write(*,'(a)') 'E D EDITING SCALE POSITIVE OK'
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
end program ede_scale_positive
