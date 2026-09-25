program i169p_len_trim_argument_controls
  implicit none
  integer, parameter :: wide_kind = selected_int_kind(18)
  character(len=5) :: scalar = 'A B'
  call require_true('len_trim accepts character string argument', len_trim(scalar) == 3)
  call require_true('len_trim kind argument is scalar integer constant', &
       kind(len_trim(scalar, kind=wide_kind)) == wide_kind)
  write(*,'(a)') 'INTRINSICS 16.9.P LEN TRIM ARGUMENT CONTROLS OK'
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
end program i169p_len_trim_argument_controls
