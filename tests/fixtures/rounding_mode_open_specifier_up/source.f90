program rm_open_specifier_up
  implicit none
! rule: S13.7.2.3.8-001
! covers: round-mode-open-specifier
  integer :: checks
  integer :: unit
  real :: open_value
  character(len=5) :: open_field
  checks = 0
  open_value = -1.25
  open(newunit=unit, file='rounding_mode_open_specifier_up.dat', status='replace', action='readwrite', form='formatted', round='UP')
  write(unit,'(SS,F5.1)') open_value
  open_field = '#####'
  call expect_text(open_field, '#####', 'sentinel-open-field')
  rewind(unit)
  read(unit,'(a)') open_field
  close(unit, status='delete')
  call expect_text(open_field, ' -1.2', 'open-up')
  if (checks /= 2) then
    write(*,'(a)') 'RM:open_specifier_up:check-total'
    error stop 1
  end if
  write(*,'(a)') 'ROUNDING MODE OPEN SPECIFIER UP OK'
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
end program rm_open_specifier_up
