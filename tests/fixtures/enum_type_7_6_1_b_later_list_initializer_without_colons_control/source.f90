program p
  implicit none
  enum, bind(c)
    enumerator :: first, second=4
  end enum
end program p
