program i169f_command_argument_count_no_args
  implicit none
  integer :: observed, command_name_control
  observed = -99
  observed = command_argument_count()
  call require_true('command_argument_count no arguments zero', observed == 0)
  command_name_control = -88
  command_name_control = command_argument_count()
  call require_true('command_argument_count command name not counted', command_name_control == 0)
  write(*,'(a)') 'INTRINSICS 16.9.F COMMAND ARGUMENT COUNT NO ARGS VALUE OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_command_argument_count_no_args
