program i169p_lgt_blank_padding
  implicit none
  character(len=1) :: short_a = 'A'
  character(len=2) :: a_exclaim = 'A!'
  call require_true('lgt blank padding lengths shorter left', &
       len(short_a) == 1 .and. len(a_exclaim) == 2)
  call require_false('lgt blank padding shorter left', lgt(short_a, a_exclaim))
  call require_true('lgt blank padding shorter right', lgt(a_exclaim, short_a))
  write(*,'(a)') 'INTRINSICS 16.9.P LGT BLANK PADDING OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169p_lgt_blank_padding
