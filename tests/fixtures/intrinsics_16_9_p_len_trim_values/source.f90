program i169p_len_trim_values
  implicit none
  character(len=5) :: trailing = 'AB'
  character(len=5) :: internal = 'A B'
  character(len=3) :: blanks = '   '
  character(len=3) :: companion = ' A '
  call require_true('len_trim removes trailing blanks', len_trim(trailing) == 2)
  call require_true('len_trim preserves internal blanks', len_trim(internal) == 3)
  call require_true('len_trim all blank string zero', &
       len_trim(blanks) == 0 .and. len_trim(companion) == 2)
  write(*,'(a)') 'INTRINSICS 16.9.P LEN TRIM VALUES OK'
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
end program i169p_len_trim_values
