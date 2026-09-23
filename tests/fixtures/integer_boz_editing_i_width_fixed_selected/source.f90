program ibe_i_width_fixed_selected
  implicit none
! rule: S13.7.2.2-001
! covers: I-width-fixed-or-selected
  integer :: checks
  integer :: value
  character(len=5) :: fixed
  character(len=2) :: selected
  checks = 0
  value = 42
  write(fixed,'(SS,I5)') value
  call expect_text(fixed, '   42', 'i5-fixed')
  write(selected,'(SS,I0)') value
  call expect_text(selected, '42', 'i0-selected')
  if (checks /= 2) then
    write(*,'(a)') 'IBE:i_width_fixed_selected:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING I WIDTH FIXED SELECTED OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'IBE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'IBE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'IBE:int', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_int
end program ibe_i_width_fixed_selected
