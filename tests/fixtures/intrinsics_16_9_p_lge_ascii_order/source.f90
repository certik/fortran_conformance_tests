program i169p_lge_ascii_order
  implicit none
  character(len=2) :: eq_a = 'Az'
  character(len=2) :: eq_b = 'Az'
  character(len=1) :: digit = '9'
  character(len=1) :: upper_a = 'A'
  character(len=1) :: upper_z = 'Z'
  character(len=1) :: underscore = '_'
  character(len=1) :: lower_a = 'a'
  call require_true('lge equal strings true', lge(eq_a, eq_b))
  call require_true('lge ascii following true', &
       lge(upper_a, digit) .and. lge(lower_a, upper_z) .and. &
       lge(lower_a, upper_a) .and. lge(underscore, upper_z))
  call require_false('lge ascii preceding false', &
       lge(digit, upper_a) .or. lge(upper_z, lower_a) .or. &
       lge(upper_a, lower_a) .or. lge(upper_z, underscore))
  write(*,'(a)') 'INTRINSICS 16.9.P LGE ASCII ORDER OK'
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
end program i169p_lge_ascii_order
