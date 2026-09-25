program p
logical :: opened
inquire(unit=10, opened=opened, err=20)
contains
subroutine target_scope()
20 continue
end subroutine target_scope
end program p
