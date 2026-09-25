program i169p_len_trim_characteristics
  implicit none
  integer, parameter :: wide_kind = selected_int_kind(18)
  character(len=4) :: scalar = 'A'
  call require_true('len_trim result is integer scalar', len_trim(scalar) == 1)
  call require_true('len_trim result kind follows kind argument or default', &
       kind(len_trim(scalar)) == kind(0) .and. kind(len_trim(scalar, kind=wide_kind)) == wide_kind)
  write(*,'(a)') 'INTRINSICS 16.9.P LEN TRIM CHARACTERISTICS OK'
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
end program i169p_len_trim_characteristics
