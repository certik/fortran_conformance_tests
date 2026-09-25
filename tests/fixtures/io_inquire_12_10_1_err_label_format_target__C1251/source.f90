program p
logical :: opened
inquire(unit=10, opened=opened, err=10)
10 format('not a branch target')
end program p
