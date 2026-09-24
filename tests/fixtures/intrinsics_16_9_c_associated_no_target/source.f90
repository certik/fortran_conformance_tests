program i169c_associated_no_target
  implicit none
  integer, target :: target_value = 47
  integer, pointer :: pointer_value
  nullify(pointer_value)
  call require_false('no target absent false iff disassociated', associated(pointer_value))
  pointer_value => target_value
  call require_true('no target absent true iff associated', associated(pointer_value))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED NO TARGET OK'
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
end program i169c_associated_no_target
