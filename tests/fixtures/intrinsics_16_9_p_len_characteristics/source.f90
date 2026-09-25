program i169p_len_characteristics
  implicit none
  integer, parameter :: wide_kind = selected_int_kind(18)
  character(len=3) :: words(2) = [character(len=3) :: 'ab', 'cd']
  call require_true('len result is scalar for array string', rank(len(words)) == 0)
  call require_true('len result kind follows kind argument or default', &
       kind(len(words)) == kind(0) .and. kind(len(words, kind=wide_kind)) == wide_kind)
  write(*,'(a)') 'INTRINSICS 16.9.P LEN CHARACTERISTICS OK'
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
end program i169p_len_characteristics
