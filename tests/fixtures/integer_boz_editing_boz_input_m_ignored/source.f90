program ibe_boz_input_m_ignored
  implicit none
! rule: S13.7.2.4-002
! covers: BOZ-input-m-ignored
  integer :: checks
  character(len=3) :: field_m, field_plain
  integer :: got_m, got_plain
  checks = 0
  field_m = '101'
  field_plain = '101'
  read(field_m,'(B3.3)') got_m
  call expect_int(got_m, 5, 'b3-m')
  read(field_plain,'(B3)') got_plain
  call expect_int(got_plain, 5, 'b3-plain')
  if (checks /= 2) then
    write(*,'(a)') 'IBE:boz_input_m_ignored:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING BOZ INPUT M IGNORED OK'
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
end program ibe_boz_input_m_ignored
