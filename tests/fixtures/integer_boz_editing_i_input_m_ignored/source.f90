program ibe_i_input_m_ignored
  implicit none
! rule: S13.7.2.2-002
! covers: I-input-m-ignored
  integer :: checks
  character(len=1) :: field_m, field_plain
  integer :: got_m, got_plain
  checks = 0
  field_m = '7'
  field_plain = '7'
  read(field_m,'(I1.1)') got_m
  call expect_int(got_m, 7, 'i1-m')
  read(field_plain,'(I1)') got_plain
  call expect_int(got_plain, 7, 'i1-plain')
  if (checks /= 2) then
    write(*,'(a)') 'IBE:i_input_m_ignored:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING I INPUT M IGNORED OK'
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
end program ibe_i_input_m_ignored
